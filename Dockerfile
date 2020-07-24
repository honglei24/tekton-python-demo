# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM harbor.ctyun.dev:1443/hl-test/python_flask:v0.1 

#RUN pip install requests --index-url https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
#CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
CMD /usr/local/bin/gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
