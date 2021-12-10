FROM python:3.9.9-bullseye

COPY ./doml_tosca_z3 /root/tosca-mc-poc
RUN pip install -r /root/tosca-mc-poc/requirements.txt
WORKDIR /root/tosca-mc-poc

CMD ["python", "-i", "-m", "doml_tosca_z3", "doml_tosca.yaml", "vttest.vt"]
