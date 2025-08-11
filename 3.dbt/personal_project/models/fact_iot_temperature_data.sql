select
    "id" as device_id,
    "room_id/id" as room_id,
    STR_TO_DATE(`noted_date`, '%d-%m-%Y %H:%i') as capture_timestamp,
    "temp" as temperature,
    "out/in" as device_location
from {{ ref('iot_temp') }}

