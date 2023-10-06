#!python3 

from flask import Flask, request
import sys
import summary
import oauth
import json
import re
import copy

app = Flask(__name__)

HTML_FORM = """MAIN <form id=form action=/ method=post>
<input type=hidden name=step id=step value=topics>
<textarea rows="20" cols="100" name=transcript>{transcript}</textarea><br>
<textarea rows="10" cols="100" name=topics_prompt>{topics_prompt}</textarea><br>
<input type="submit" value="topics">
<input value="run all" type="button" onclick='document.getElementById("step").value = "runall"; document.getElementById("form").submit()'>

<p>
<a href=#topics></a>
<textarea rows="20" cols="100" name=topics>{topics}</textarea><br>
<textarea rows="10" cols="100" name=summaries_prompt>{summaries_prompt}</textarea><br>
<input value="summaries" type="button" onclick='document.getElementById("form").action = "/#summaries"; document.getElementById("step").value = "summaries"; document.getElementById("form").submit()'>

<p>
<textarea rows="20" cols="100" name=summaries>{summaries}</textarea><br>
<a href=#summaries></a>
<textarea rows="10" cols="100" name=companies_prompt>{companies_prompt}</textarea><br>
<input value="companies" type="button" onclick='document.getElementById("form").action = "/#results"; document.getElementById("step").value = "companies"; document.getElementById("form").submit()'>
<p>
<a href=#results></a>
{results}
<p>
<textarea hidden=hidden name=hidden_results>{results}</textarea><br>
<a href=#edits></a>
<textarea rows="10" cols="100" name=edits_prompt>{edits_prompt}</textarea><br>
<input value="Suggested Edits?" type="button" onclick='document.getElementById("form").action = "/#edits"; document.getElementById("step").value = "edits"; document.getElementById("form").submit()'>
<p>
<div>
{edited_results}
</div>
"""

BLURB_HTML = """<b>{topic}</b>:<br>
                  <i>{people}; {companies}</i><br>{topic_summary}<p>"""

def parseJSONEmptyIfNone(text):
    return json.loads(text) if text else ""

def dumpJSONEmptyIfNone(j):
    return json.dumps(j, indent=2) if j and len(j) > 0 else ""

@app.route("/", methods=["POST", "GET"])
def handle_request():
    data = request
    
    transcript = request.form.get('transcript') if request.form.get('topics_prompt') else ""

    topics_prompt = request.form.get('topics_prompt') if request.form.get('topics_prompt') else summary.TOPICS_PROMPT
    summaries_prompt = request.form.get('summaries_prompt') if request.form.get('summaries_prompt') else summary.SUMMARIES_PROMPT
    companies_prompt = request.form.get('companies_prompt')
    edits_prompt = request.form.get('edits_prompt') if request.form.get('edits_prompt') else summary.EDITS_PROMPT
    company_annotated_results = request.form.get('hidden_results') if request.form.get('hidden_results')  else ""
    edited_results = ""
    
    topics = parseJSONEmptyIfNone(request.form.get('topics'))
    summaries = parseJSONEmptyIfNone(request.form.get('summaries'))
    
    step = request.form.get('step')
    
    print(f"Step={step}", file=sys.stderr)
    if step == "topics" or step == "runall":

        # stip the time codes
        regex = re.compile(r'^[0-9]')
        lines = transcript.splitlines()
        clean_lines = [line for line in lines if not regex.match(line)]
        transcript = "\n".join(clean_lines)

        topics = summary.get_topics(transcript, topics_prompt)
        summaries = ''
        company_annotated_results = ''

    if step == "summaries" or step == "runall":
        summaries = summary.add_summaries(extracted_topics=copy.deepcopy(topics), prompt_text=summaries_prompt, transcript=transcript)
        company_annotated_results = ''

    if step == "companies" or step == "runall":
        company_annotated = summary.add_company_annotations(summarized_topics=copy.deepcopy(summaries), prompt_text=companies_prompt, transcript=transcript)
        blurbs = []
        for s in company_annotated:
            topic = s['Topic']
            people = s['People']
            topic_summary = s['Summary']
            companies = s['Companies']
    
            blurb = BLURB_HTML.format(topic=topic, companies=companies, topic_summary=topic_summary, people=people)
            blurbs.append(blurb)
        company_annotated_results = '\n'.join(blurbs)

    if step == "edits":
        print(f"Running EDITS step")
        edited_results = summary.get_edits(prompt_text=edits_prompt, transcript=transcript, summary=company_annotated_results)

    res = HTML_FORM.format(transcript=transcript, 
                            topics_prompt = topics_prompt,
                            summaries_prompt = summaries_prompt,
                            topics=dumpJSONEmptyIfNone(topics), 
                            summaries=dumpJSONEmptyIfNone(summaries), 
                            companies_prompt = summary.COMPANIES_PROMPT,
                            results=company_annotated_results,
                            edits_prompt = edits_prompt,
                            edited_results=edited_results)
    return res

if __name__ == "__main__":
  app.run(host='0.0.0.0', port='5001', debug=True)

  