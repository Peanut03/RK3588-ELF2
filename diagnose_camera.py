#!/usr/bin/env python3

import cv2
import os

def diagnose_cameras():
    available_cameras = []
    
    for index in range(30):
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        
        if cap is None or not cap.isOpened():
            if cap:
                cap.release()
            continue
            
        ret, frame = cap.read()
        
        if ret:
            filename = f"capture_test_{index}.jpg"
            try:
                cv2.imwrite(filename, frame)
                available_cameras.append(index)
            except Exception as e:
                pass
        else:
            pass
            
        cap.release()

if __name__ == "__main__":
    diagnose_cameras() 