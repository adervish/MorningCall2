import re
import json
import re
import sys
import argparse
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

anthropic = Anthropic(api_key='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')

TOPICS_PROMPT = """{HUMAN_PROMPT} Here is a transcript, in <transcript></transcript> XML tags:
<transcript>{transcript}</transcript>
List the main topics discussed in the Transcript and primary people who participated in each discussion 
Answer in JSON only. The JSON should be only a list of dictionaries whose keys are "Topic" and "People" 
{AI_PROMPT}
"""

EDITS_PROMPT = """{HUMAN_PROMPT} 
Please edit the following summary of a transcript and 


<summary>{summary}</summary>

{AI_PROMPT}
"""

SUMMARIES_PROMPT = """{HUMAN_PROMPT} Transcript: {{{{{transcript}}}}}

One of our memebers was not able to attend this morning's conference call. 

You will generate concise, entity-dense summary of the the discussion of topic {topic} in the above transcript

The response should be contained in <summary></summary> XML tags

Guidelines:
- faithful only include facts from the Transcript 
- the summary should be no more than 4 - 5 sentances, about 100 words 

{AI_PROMPT}"""

COMPANIES_PROMPT = """{HUMAN_PROMPT} Transcript: {{{{{transcript}}}}}

Read the aboce transcript and print a list of the companies mentioned in the discussion of the topic {topic} if the company is public, please include the ticker symbol as well as the name of the company

Answer in JSON only. The JSON should be only a list of dictionaries whose keys are "Name" and "Ticker" 

Guidelines:
- faithful only include facts from the Transcript 

{AI_PROMPT}"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--topics', type=argparse.FileType('r'), help='file with JSON of the topics')
    parser.add_argument('--company_annotated', type=argparse.FileType('r'), help='file with JSON of the company annotated topics')
    parser.add_argument('--summarized_topics', type=argparse.FileType('r'), help='file with JSON of the summarized topics')
    parser.add_argument('--write_topics', type=argparse.FileType('w'), help='write intermediate responses')
    parser.add_argument('--write_company_annotated', type=argparse.FileType('w'), help='write intermediate responses')
    parser.add_argument('--write_summarized_topics', type=argparse.FileType('w'), help='write intermediate responses')
    parser.add_argument('--transcript', type=argparse.FileType('r'), help='transcript to process')

    args = parser.parse_args()

    blurbs = doIt(args=args)
    print( '\n'.join(blurbs))

def jsonheaderawareloads(s):
    print (f"Text={s}")
    regex = r".*?(\[.*])"
    match = re.search(r'.*?(\[.*])', s, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    else:
        return json.loads(s) 

def doIt(args=None, transcript_file=None):

    print(AI_PROMPT, file=sys.stderr)

    extracted_topics = None
    if args.topics:
        print("read topics", file=sys.stderr)
        extracted_topics = json.loads(args.topics.read())

    summarized_topics = None
    if args.summarized_topics:
        summarized_topics = json.loads(args.summarized_topics.read())

    company_annotated = None
    if args.company_annotated:
        company_annotated = json.loads(args.company_annotated.read())

    transcript = args.transcript.read()
    
    if not extracted_topics:
        extracted_topics = get_topics(transcript, TOPICS_PROMPT)
        if args.write_topics:
            args.write_topics.write(json.dumps(extracted_topics, indent=4))
            print(f"wrote topics to {args.write_topics}", file=sys.stderr)

    if not summarized_topics:
        summarized_topics = add_summaries(extracted_topics, SUMMARIES_PROMPT, transcript)
        if args.write_summarized_topics:
            args.write_summarized_topics.write(json.dumps(summarized_topics, indent=4))
            print(f"wrote summarized_topics to {args.write_summarized_topics}", file=sys.stderr)

    if not company_annotated:
        company_annotated = add_company_annotations(summarized_topics, COMPANIES_PROMPT, transcript)
        if args.write_company_annotated:
            args.write_company_annotated.write(json.dumps(company_annotated, indent=4))
            print(f"wrote company_annotated to {args.write_company_annotated}", file=sys.stderr)

    blurbs = []
    for s in company_annotated:
        topic = s['Topic']
        people = s['People']
        summary = s['Summary']
        companies = s['Companies']
    
        blurb = f"""<b>{topic}</b>:<br>
                <i>{people}; {companies}</i><br>{summary}<p>"""
        blurbs.append(blurb)
    return blurbs

def get_topics(transcript, prompt_text):
    prompt = prompt_text.format(HUMAN_PROMPT=HUMAN_PROMPT, AI_PROMPT=AI_PROMPT, transcript=transcript)
    completion = anthropic.completions.create(
        model="claude-2",
        max_tokens_to_sample=500,
        prompt=prompt,
    )
    extracted_topics = jsonheaderawareloads( completion.completion )
    print(json.dumps(extracted_topics, indent=4), file=sys.stderr)
    return extracted_topics

def get_edits(prompt_text, transcript, summary):
    prompt = prompt_text.format(HUMAN_PROMPT=HUMAN_PROMPT, AI_PROMPT=AI_PROMPT, transcript=transcript, summary=summary)

    print(f"-------------\nGET EDITS PROMPT {prompt}\n-------------\n")

    completion = anthropic.completions.create(
        model="claude-2",
        max_tokens_to_sample=2000,
        prompt=prompt,
    )
    edited_text = completion.completion 
    return edited_text

def add_summaries(extracted_topics, prompt_text, transcript):
    results = []
    for t in extracted_topics:
        topic = t['Topic']
        people = t['People']
        prompt = prompt_text.format(HUMAN_PROMPT=HUMAN_PROMPT, AI_PROMPT=AI_PROMPT, topic=topic, transcript=transcript)

        completion = anthropic.completions.create(
            model="claude-2",
            max_tokens_to_sample=300,
            prompt=prompt,
        )
        match = re.search(r'.*?<summary>(.*)</summary>', completion.completion, re.DOTALL)
        #t.append(match.group(1))
        t['Summary'] = match.group(1)
        results.append(t)
    print(json.dumps(results, indent=4), file=sys.stderr)
    return results

def add_company_annotations(summarized_topics, prompt_text, transcript):
    results = []
    for t in summarized_topics:
        topic = t['Topic']
        people = t['People']
        prompt = prompt_text.format(HUMAN_PROMPT=HUMAN_PROMPT, AI_PROMPT=AI_PROMPT, topic=topic, transcript=transcript)

        completion = anthropic.completions.create(
            model="claude-2",
            max_tokens_to_sample=300,
            prompt=prompt,
        )

        companies = jsonheaderawareloads( completion.completion )

        company_text = ""
        for c in companies:
            name = c['Name']
            if 'Ticker' in c:
                ticker = f"<a href='https://drill.gghc.com/security_detail.aspx?sec_alias={c['Ticker']}'>{c['Ticker']}</a>"
            else:
                ticker = ""

            company_text = f"{company_text} {name} #{ticker}"
        t['Companies'] = company_text
        results.append(t)
        print(json.dumps(results, indent=4), file=sys.stderr)
    return(results)

if __name__ == "__main__":
  main()



