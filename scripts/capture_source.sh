#!/usr/bin/env bash
set -euo pipefail
wget --mirror --page-requisites --adjust-extension --convert-links --no-parent \
  --span-hosts --domains=proimmunesystem.wordpress.com,s0.wp.com,s1.wp.com,s2.wp.com,i0.wp.com,i1.wp.com,i2.wp.com,fonts.wp.com,proimmunesystem.files.wordpress.com \
  -e robots=off -P _source https://proimmunesystem.wordpress.com/
