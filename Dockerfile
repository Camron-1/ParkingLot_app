FROM python:3.12

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg \
       python3-tk \
       x11-apps \
       libgl1 \
       libsm6 \
       libxext6 \
       libxrender1 \
       nodejs \
       npm \
       fonts-dejavu-core \
       fontconfig \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY . ./

ENV DISPLAY=host.docker.internal:0
ENV QT_QPA_FONTDIR=/usr/share/fonts/truetype/dejavu
CMD ["sh", "-c", "exec python3 main.py --url \"$YOUTUBE_URL\""]