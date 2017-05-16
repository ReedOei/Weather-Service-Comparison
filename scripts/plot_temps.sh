cd ..

if [ -z "$1" ]; then
    METHOD="decay"
else
    METHOD="$1"
fi

if [ -z "$2" ]; then
    ANALYZE_DIR="./analyze/daily/"
else
    ANALYZE_DIR="./analyze/$2/"
fi

python collect_data.py combine o=forecast.txt analyze_dir="$ANALYZE_DIR" method="$METHOD"
python collect_data.py dump graph show_actual analyze_dir=./analyze/currently/ f=forecast.txt var=temp_max,temp_min,temp minvar=temp_min maxvar=temp_max
