


===============================
Google Sheet Import API
===============================

The module adds the possibility to import data and create fields from Google Spreadsheets in odoo.

Major Issues
============

* When We Export Any Data From Odoo To Google Sheet And After That We import Same file Some Fields Data Are not Import 
  And Throw Error.
* The Date And Datetime Fields Data Are not Proper Import And Export.
* Many2one Fields Data not Import Proper When We import Sheet IF Any data Has no record In Many2one Field.

Major Fixed Issues
==================

* Fix And Solved Date And Datetime Field Import Code.
* Fix And Solved Many2one Field Import Code.
* On The OtherHand We Fix Some Other Problems.