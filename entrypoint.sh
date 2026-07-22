#!/bin/sh

# Áp dụng thay đổi database
echo "Running database migrations..."
python manage.py migrate --noinput

# Nạp dữ liệu mẫu seed data
echo "Seeding initial movie and cinema data..."
python manage.py seed_data

# Khởi động server Django
echo "Starting Django Server on 0.0.0.0:8000..."
exec python manage.py runserver 0.0.0.0:8000
