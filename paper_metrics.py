"""Text measurement for the paper's six F1–F3 measures and F5–F8 form sources.

Learner text is not bundled. Call these functions only with material you are
authorized to process. The output contains numerical summaries and no source text.
"""
from __future__ import annotations
import math
import re
import unicodedata
from kiwipiepy import Kiwi

PUNCTUATION_TAGS={"SF","SP","SS","SSO","SSC","SE","SO","SW"}
PREDICATE_PREFIXES=("VV","VA","VX","VCP","VCN")


def normalize_text(value:object)->str:
    if value is None or isinstance(value,float) and math.isnan(value):return ""
    return unicodedata.normalize("NFC",str(value)).replace("\r\n","\n").replace("\r","\n").strip()


def eojeol_count(text:str)->int:
    return sum(bool(re.search(r"[가-힣A-Za-z0-9]",part)) for part in re.findall(r"\S+",normalize_text(text)))


def mattr20(types:list[str])->float|None:
    if not types:return None
    if len(types)<20:return len(set(types))/len(types)
    return sum(len(set(types[i:i+20]))/20 for i in range(len(types)-19))/(len(types)-19)


def measure_text(text:str,kiwi:Kiwi|None=None)->tuple[dict,set]:
    """Return only the six manuscript measures, a short-text flag, and form types."""
    text=normalize_text(text)
    kiwi=kiwi or Kiwi(num_workers=-1)
    sentences=[s.text.strip() for s in kiwi.split_into_sents(text) if s.text.strip()]
    if not sentences and text:sentences=[text]
    tokens=[(t.form,t.tag) for t in kiwi.tokenize(text)
            if t.tag and t.tag not in PUNCTUATION_TAGS and not t.tag.startswith(("W","Z"))]
    types=[f"{form}/{tag}" for form,tag in tokens]
    forms=set(zip(types,types[1:]))
    words=eojeol_count(text);n_sent=len(sentences)
    pred=sum(tag.startswith(PREDICATE_PREFIXES) for _,tag in tokens)
    result={
        "characters":sum(ch.isalnum() for ch in text),
        "eojeols":words,"sentences":n_sent,"mattr20":mattr20(types),
        "mean_sentence_length":words/n_sent if n_sent else None,
        "predicates_per_sentence":pred/n_sent if n_sent else None,
        "mattr_short_ttr":0<len(types)<20,
    }
    return result,forms


def form_source_metrics(a:set,b:set,c:set)->dict:
    ua=a-b;ub=b-a;retained=ua&c;borrowed=ub&c;new=c-(a|b)
    ra=len(retained)/len(ua) if ua else None
    rb=len(borrowed)/len(ub) if ub else None
    nc=len(new)/len(c) if c else None
    proximity=None if ra is None or rb is None else (rb-ra)/(rb+ra) if rb+ra else 0.
    return {"retention_ra":ra,"borrowing_rb":rb,"novelty_nc":nc,"proximity_p":proximity,
        "a_unique_bigrams":len(ua),"b_unique_bigrams":len(ub),"c_bigrams":len(c),
        "a_retained_bigrams":len(retained),"b_borrowed_bigrams":len(borrowed),"c_new_bigrams":len(new)}
