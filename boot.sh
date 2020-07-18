#!/bin/bash
exec gunicorn -w 2 -b 0.0.0.0:6000 manage:app