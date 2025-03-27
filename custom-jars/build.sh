#!/bin/bash
set -e

for jar in */ ; do
    echo "Building JAR for ${jar%/}"
    cd $jar
    zip -r ../${jar%/}.jar META-INF/ *.js
    cd ..
done
