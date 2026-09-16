#!/bin/bash
cd backend
pip install -r requirements.txt -q
echo 'Starting quantum swarm simulation...'
echo 'Open http://localhost:8000 in your browser'
uvicorn main:app --reload
