let
  pkgs = import (builtins.getFlake "nixpkgs").outPath {};
in pkgs.texlive.combine {
  inherit (pkgs.texlive)
    scheme-small fontspec mathfont siunitx pgf float was
    booktabs tools amscls hyperref xurl microtype;
}
