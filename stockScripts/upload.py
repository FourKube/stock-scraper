#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Use text editor to edit the script and type in valid Instagram username/password

from InstagramAPI import InstagramAPI

InstagramAPI = InstagramAPI("wackerboys77", "rushhour1")
InstagramAPI.login()  # login

photo_path = 'ridgeplot.jpg'
caption = "Sample photo"

InstagramAPI.uploadPhoto(photo_path, caption=caption)
