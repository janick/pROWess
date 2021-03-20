##
## Copyright (c) 2017-2021 Janick Bergeron  <janick@bergeron.com>
## All Rights Reserved
##
##   Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in
##   compliance with the License.  You may obtain a copy of the License at
##
##       http://www.apache.org/licenses/LICENSE-2.0
##
##   Unless required by applicable law or agreed to in writing, software distributed under the License is
##   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##   See the License for the specific language governing permissions and limitations under the License.
##

SKILL	= MyRower

ZIP	= $(PWD)/$(SKILL).zip

all install upload: compile
	rm -f $(ZIP)
	cd py && zip $(ZIP) lambda_function.py
#	( cd venv/lib/python2.7/site-packages; zip -r $(ZIP) requests certifi chardet idna urllib3 )
	aws lambda update-function-code --function-name $(SKILL) --zip-file fileb://$(ZIP)

publish:
	aws lambda publish-version --function-name $(SKILL)

update:
	aws lambda update-alias --function-name $(SKILL) --name REL2 --function-version $(VER)

compile:
	python3 py/lambda_function.py

clean:
	rm -rf *~ *.zip
