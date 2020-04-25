FROM python:3.7-alpine
RUN apk --no-cache add git openssh
COPY git-cleanup-branches.py /
WORKDIR /workdir
ENTRYPOINT ["python3","-u","/git-cleanup-branches.py"]
