{ }:

with import <nixpkgs> {};

let
  python = python26;
  pythonPackages = python26Packages;
  base = import ./base.nix {
    inherit python pythonPackages;
    pythonDocs = pythonDocs.html.python26;
  };

in

buildEnv {
  name = "dev-env";
  ignoreCollisions = true;
  paths = [
    (openldap.override { cyrus_sasl = null; openssl = null; })
    pythonPackages.ldap
    pythonPackages.ordereddict
    pythonPackages.zope_interface
  ] ++ base.paths;
}
