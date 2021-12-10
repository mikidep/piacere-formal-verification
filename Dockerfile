FROM python:3.9.9-bullseye

RUN apt-get update && \
    apt-get install -y swi-prolog

COPY ./doml_tosca_poc /root/tosca-mc-poc
RUN pip install -r /root/tosca-mc-poc/requirements.txt
WORKDIR /root/tosca-mc-poc

CMD ["python", "-i", "poc.py", "doml_tosca.yaml"]
