cd ..

if [ -z "$2" ]; then
    ANALYZE_DIR="./analyze/daily/"
else
    ANALYZE_DIR="./analyze/$2/"
fi

SERVICES="darksky yahoo accuweather wunderground openweathermap"
METHODS="decay first last average median"

rm data.csv

for service in $SERVICES
do
    echo "Aggregating data from $service"
    python collect_data.py aggregate re="$service"
    for method in $METHODS
    do
        python collect_data.py combine o="analyze/method/$method.txt" analyze_dir="$ANALYZE_DIR" method="$method"
        python collect_data.py dump graph o="data.csv" analyze_dir=./analyze/currently/ f="analyze/method/$method.txt" var=temp_max,temp_min,temp minvar=temp_min maxvar=temp_max
    done
done
