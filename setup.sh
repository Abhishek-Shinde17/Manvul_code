#!/bin/bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
echo 'Done! Run: python manage.py runserver'
