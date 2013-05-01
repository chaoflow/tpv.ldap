LOCALISED_SCRIPTS = ipython ipdb flake8 pylint nose
PROJECT = $(shell basename $(shell pwd))

PYTHON_VERSION = 2.6
NIX_PROFILE = ./nixprofile${PYTHON_VERSION}
NIX_SITE = ${NIX_PROFILE}/lib/python${PYTHON_VERSION}/site-packages
VENV_CMD = ${NIX_PROFILE}/bin/virtualenv
VENV = .
VENV_SITE = ${VENV}/lib/python${PYTHON_VERSION}/site-packages
SLAPD = ${NIX_PROFILE}/libexec/slapd
SLAPADD = ${NIX_PROFILE}/sbin/slapadd
NOSETESTS = SLAPD=${SLAPD} SLAPADD=${SLAPADD} ${VENV}/bin/nosetests


# loglevels for SLAPD_LOGLEVEL, comma-separated
# 1      (0x1 trace) trace function calls
# 2      (0x2 packets) debug packet handling
# 4      (0x4 args) heavy trace debugging (function args)
# 8      (0x8 conns) connection management
# 16     (0x10 BER) print out packets sent and received
# 32     (0x20 filter) search filter processing
# 64     (0x40 config) configuration file processing
# 128    (0x80 ACL) access control list processing
# 256    (0x100 stats) connections, LDAP operations, results (recommended)
# 512    (0x200 stats2) stats log entries sent
# 1024   (0x400 shell) print communication with shell backends
# 2048   (0x800 parse) entry parsing

export SLAPD_LOGLEVEL := stats
export KEEP_FAILED := 1

all: check

bootstrap: dev.nix requirements.txt setup.py
	nix-env -p ${NIX_PROFILE} -i dev-env -f dev${PYTHON_VERSION}.nix
	${VENV_CMD} --distribute --clear .
	realpath --no-symlinks --relative-to ${VENV_SITE} ${NIX_SITE} > ${VENV_SITE}/nixprofile.pth
	${VENV}/bin/pip install -r requirements.txt --no-index -f ""
	for script in ${LOCALISED_SCRIPTS}; do ${VENV}/bin/easy_install -H "" $$script; done

print-syspath:
	${VENV}/bin/python -c 'import sys,pprint;pprint.pprint(sys.path)'


var:
	test -L var -a ! -e var && rm var || true
	ln -s $(shell mktemp --tmpdir -d ${PROJECT}-var-XXXXXXXXXX) var

var-clean:
	rm -fR var/*

check: var var-clean
	${NOSETESTS} -v -w . --processes=4 ${ARGS}

check-debug: var var-clean
	DEBUG=1 ${NOSETESTS} -v -w . --ipdb --ipdb-failures ${ARGS}

coverage: var var-clean
	rm -f .coverage
	${NOSETESTS} -v -w . --with-cov --cover-branches --cover-package=${PROJECT} ${ARGS}


pyoc-clean:
	find . -name '*.py[oc]' -print0 |xargs -0 rm

update-ldap-schema:
	mkdir -p etc/openldap/schema
	cp ${NIX_PROFILE}/etc/openldap/schema/* etc/openldap/schema/

.PHONY: all bootstrap check coverage print-syspath pyoc-clean test-nose var var-clean
