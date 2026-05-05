#!/bin/sh

IMG_FILE=~/aps08_postgres_disk.img
MOUNT_POINT="/mnt/wsl/aps08_rds_sim"
INITIAL_SIZE="300M"
SCALE_STEP="100M"
THRESHOLD=80

set -e

echo "[APS08] Verifying tools..."
for tool in truncate losetup mkfs.ext4 mount umount awk sed stat df resize2fs; do
    if ! command -v $tool >/dev/null 2>&1; then
        echo "[APS08] ERROR: Required tool '$tool' not found. Check your installation."
        exit 1
    fi
done

echo "[APS08] Starting Storage Manager..."

cleanup() {
    echo "[APS08] Received shutdown signal. Cleaning up..."
    umount $MOUNT_POINT 2>/dev/null || true
    DISK_DEVICE=$(losetup -j "$IMG_FILE" | cut -d: -f1)
    if [ ! -z "$DISK_DEVICE" ]; then
        losetup -d "$DISK_DEVICE"
        echo "[APS08] Detached $DISK_DEVICE"
    fi
    rm -rf "$IMG_FILE"
    echo "[APS08] Removed $IMG_FILE. Cleanup complete."
    exit 0
}

trap cleanup SIGTERM SIGINT

echo "[APS08] Cleaning up stale state..."
umount "$MOUNT_POINT" 2>/dev/null || true

STALE_LOOP=$(losetup -j "$IMG_FILE" | cut -d: -f1)
if [ ! -z "$STALE_LOOP" ]; then
    echo "[APS08] Detaching stale loop device $STALE_LOOP..."
    losetup -d "$STALE_LOOP"
fi

if [ -f "$IMG_FILE" ]; then
    echo "[APS08] Removing old image file to ensure fresh start..."
    rm -f "$IMG_FILE"
fi

echo "[APS08] Creating initial disk image ($INITIAL_SIZE)..."
truncate -s $INITIAL_SIZE "$IMG_FILE"

DISK_DEVICE=$(losetup -f)
echo "[APS08] Attaching to loop device $DISK_DEVICE..."
losetup "$DISK_DEVICE" "$IMG_FILE"

echo "[APS08] Formatting as EXT4..."
mkfs.ext4 "$DISK_DEVICE"

echo "[APS08] Ensuring mount point $MOUNT_POINT exists..."
mkdir -p "$MOUNT_POINT"

echo "[APS08] Mounting $DISK_DEVICE to $MOUNT_POINT..."
mount "$DISK_DEVICE" "$MOUNT_POINT"

echo "[APS08] Setting permissions (UID 999)..."
chown 999:999 "$MOUNT_POINT"

echo "[APS08] Storage is READY."

RESIZE_BIN=$(command -v resize2fs)

while true; do
    USAGE_PCT=$(df "$MOUNT_POINT" | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$USAGE_PCT" -ge "$THRESHOLD" ]; then
        echo "[APS08-AUTOSCALE] Usage reached ${USAGE_PCT}%. Scaling up by ${SCALE_STEP}..."
        
        CUR_BYTES=$(stat -c %s "$IMG_FILE")
        NEW_BYTES=$((CUR_BYTES + 104857600))
        
        truncate -s "$NEW_BYTES" "$IMG_FILE"
        
        DISK_DEVICE=$(losetup -j "$IMG_FILE" | cut -d: -f1)
        losetup -c "$DISK_DEVICE"
        $RESIZE_BIN "$DISK_DEVICE"
        
        NEW_SIZE=$(df -h "$MOUNT_POINT" | tail -1 | awk '{print $2}')
        echo "[APS08-AUTOSCALE] Success! New capacity: $NEW_SIZE"
    fi
    
    sleep 5
    echo "[APS08] Storage usage: ${USAGE_PCT}%"
done
