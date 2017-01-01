if [ -z "$1" ]; then
    VAR="precip_chance"
else
    VAR="$1"
fi

if [ -z "$2" ]; then
    ANALYZE_DIR="./analyze/daily/"
else
    ANALYZE_DIR="./analyze/$2/"
fi

python collect_data.py dump graph=True var="$VAR" analyze_dir="$ANALYZE_DIR" type=box
