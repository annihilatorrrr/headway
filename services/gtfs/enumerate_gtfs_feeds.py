import os
from urllib.request import urlopen
import requests
import csv

def extract_column(name_row, data_row, wanted_column):
  try:
    column_index = name_row.index(wanted_column)
    return None if column_index >= len(data_row) else data_row[column_index]
  except ValueError:
    return None

def extract_column_float(name_row, data_row, wanted_column):
  try:
    str_val = extract_column(name_row, data_row, wanted_column)
    return None if str_val is None or str_val == '' else float(str_val)
  except ValueError:
    return None

def gtfs_line_intersects(name_row, data_row, bbox):
  min_long = extract_column_float(name_row, data_row, 'location.bounding_box.minimum_longitude')
  max_long = extract_column_float(name_row, data_row, 'location.bounding_box.maximum_longitude')
  min_lat = extract_column_float(name_row, data_row, 'location.bounding_box.minimum_latitude')
  max_lat = extract_column_float(name_row, data_row, 'location.bounding_box.maximum_latitude')

  if min_long is None or max_long is None or min_lat is None or max_lat is None:
    return False

  if max_lat - min_lat > 18 or max_long - min_long > 16:
    # This almost certainly just means the transit provider operates "everywhere".
    return False

  # Thers's probably a better way to do this but it's a sunday morning and I haven't had coffee yet.
  if max_long < bbox[0] or max_lat < bbox[1]:
    return False
  return False if min_lat > bbox[3] else min_long <= bbox[2]

try:
  bbox = [float(val) for val in os.environ['HEADWAY_BBOX'].strip().split(' ')]
  if len(bbox) != 4:
    raise ValueError('Length != 4')
except:
  print('Invalid or missing environment variable HEADWAY_BBOX')
  raise

gtfs_url = 'https://storage.googleapis.com/storage/v1/b/mdb-csv/o/sources.csv?alt=media'
gtfs_feed_text = urlopen(gtfs_url).read().decode('utf-8')

gtfs_lines = [row for row in csv.reader(gtfs_feed_text.split('\n'), delimiter=',', quotechar='"') if len(row) > 0]
gtfs_name_line = gtfs_lines[0]
gtfs_data_lines = gtfs_lines[1:]

matching_lines = [line for line in gtfs_data_lines if gtfs_line_intersects(gtfs_name_line, line, bbox)]

with open('/gtfs_feeds/gtfs_feeds.csv', 'w') as f:
  w = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
  for line in matching_lines:
    if extract_column(gtfs_name_line, line, 'data_type') == 'gtfs':
      w.writerow([
        extract_column(gtfs_name_line, line, 'provider'),
        extract_column(gtfs_name_line, line, 'mdb_source_id'),
        extract_column(gtfs_name_line, line, 'urls.latest')])
