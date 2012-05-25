;;; zeroein.el --- Zero setup Emacs IPython Notebook client

;; Copyright (C) 2012- Takafumi Arakaki

;; Author: Takafumi Arakaki

;; This file is NOT part of GNU Emacs.

;; zeroein.el is free software: you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation, either version 3 of the License, or
;; (at your option) any later version.

;; zeroein.el is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with zeroein.el.  If not, see <http://www.gnu.org/licenses/>.

;;; Commentary:

;;

;;; Code:

(defvar zeroein:root-dir
  (or (if load-file-name (file-name-directory load-file-name))
      default-directory))

(defun zeroein:path (p &rest ps)
  (if ps
      (apply #'zeroein:path
           (concat (file-name-as-directory p) (car ps)) (cdr ps))
    (concat zeroein:root-dir p)))

(mapc (lambda (path) (add-to-list 'load-path (zeroein:path path)))
      '("ein" "markdown-mode" "websocket" "python" "auto-complete"
        "popup" "fuzzy" "pos-tip" "smartrep"))

(load (zeroein:path "nxhtml" "autostart.el"))

(require 'ein)
(ein:notebooklist-open)


;; Suppress this warning when using mumamo:
;; Warning: `font-lock-syntactic-keywords' is an obsolete variable (as of 24.1);
;;     use `syntax-propertize-function' instead.
(when (and (equal emacs-major-version 24)
           (equal emacs-minor-version 1))
  (eval-after-load "bytecomp"
    '(add-to-list 'byte-compile-not-obsolete-vars
                  'font-lock-syntactic-keywords)))
;; See: http://stackoverflow.com/a/5470584/727827

;;; zeroein.el ends here
