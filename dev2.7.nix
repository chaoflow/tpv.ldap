{ }:

with import <nixpkgs> {};

let
  python = python27;
  pythonPackages = python27Packages;
  base = import ./base.nix {
    inherit python pythonPackages;
    pythonDocs = pythonDocs.html.python27;
  };

in

buildEnv {
  name = "dev-env";
  ignoreCollisions = true;
  paths = [
    (openldap.override { cyrus_sasl = null; openssl = null; })
    pythonPackages.ldap
    pythonPackages.zope_interface
  ] ++ base.paths;
}
