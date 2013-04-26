{ }:

let
  base = import ./base.nix { };

in

with import <nixpkgs> {};

buildEnv {
  name = "dev-env";
  ignoreCollisions = true;
  paths = [
    (openldap.override { cyrus_sasl = null; openssl = null; })
    python26Packages.ldap
    python26Packages.ordereddict
    python26Packages.zope_interface
  ] ++ base.paths26;
}