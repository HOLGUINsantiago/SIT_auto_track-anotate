#!/bin/bash
sleap-track D:\SIT_auto\SLEAP\labels.v001.slp --only-suggested-frames -m models\250626_163235.centroid -m models\250626_163235.centered_instance --controller_port 9000 --publish_port 9001 --max_instances 2 -o labels.v001.slp.predictions.slp --verbosity json --no-empty-frames
