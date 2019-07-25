FROM joyzoursky/python-chromedriver:3.7-selenium
# chrome debug port https://developers.google.com/web/updates/2017/04/headless-chrome#frontend
EXPOSE 9222/tcp
ARG  pypi
ENV  pypi=$pypi
ARG  omegaml_version
ENV  omegaml_version=$omegaml_version
WORKDIR /root
COPY ./packages /var/packages
RUN  pip install --upgrade pip -q
RUN  pip install --ignore-installed six -f /var/packages -i $pypi --extra-index-url https://pypi.org/simple/ omegaml==$omegaml_version && \
     pip install behave splinter

