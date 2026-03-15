set -e

echo "Required ~330GB disk space for template data"


# if cache_dir is not set, use "./cache_data" by default
if [ -z "$cache_dir" ]; then
    cache_dir="./cache_data"
fi
mkdir -p "$cache_dir"
mkdir -p "$cache_dir/common"
mkdir -p "$cache_dir/search_database"

if command -v aria2c &> /dev/null; then
    aria2c -c -x 10 -s 10 -k 1M -o "$cache_dir/mmcif.tar.gz" https://protenix.tos-cn-beijing.volces.com/mmcif.tar.gz
    aria2c -c -x 10 -s 10 -k 1M -o "$cache_dir/common/release_date_cache.json" https://protenix.tos-cn-beijing.volces.com/common/release_date_cache.json
    aria2c -c -x 10 -s 10 -k 1M -o "$cache_dir/common/obsolete_to_successor.json" https://protenix.tos-cn-beijing.volces.com/common/obsolete_to_successor.json
else
    wget -P "$cache_dir" https://protenix.tos-cn-beijing.volces.com/mmcif.tar.gz
    wget -P "$cache_dir/common" https://protenix.tos-cn-beijing.volces.com/common/release_date_cache.json
    wget -P "$cache_dir/common" https://protenix.tos-cn-beijing.volces.com/common/obsolete_to_successor.json
fi

# Extract mmcif.tar.gz to $cache_dir/mmcif
mkdir -p "$cache_dir/mmcif"
tar -xzf "$cache_dir/mmcif.tar.gz" -C "$cache_dir/mmcif"