#Step 1 - Install base image
FROM python:3.10.1-alpine3.14

#Step 2 - Define cwd
WORKDIR /app

#Step 3 - Copy over any dependencies
COPY requirements.txt requirements.txt

#Step 4 - Actually install dependencies
RUN pip3 install -r requirements.txt

#Step 5 - Copy source code
COPY . .

#Step 6 - Default run command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]