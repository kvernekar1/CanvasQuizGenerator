import json
import uuid
import zipfile
import random
import re
from xml.etree.ElementTree import Element, SubElement, indent, tostring

def _make_ident() -> str:
    return "g" + uuid.uuid4().hex[:12]


def _make_answer_id() -> str:
    return str(random.randint(1000, 9999))


def _extract_answer_letter(raw: str) -> str:
    match = re.search(r'[A-Za-z]', raw)
    return match.group(0).upper() if match else raw.strip().upper()


def _item_metadata(item_el: Element, qtype: str, points: int = 1) -> None:
    meta = SubElement(item_el, "itemmetadata")
    qtimeta = SubElement(meta, "qtimetadata")
    for label, entry in [("question_type", qtype), ("points_possible", str(points))]:
        field = SubElement(qtimeta, "qtimetadatafield")
        SubElement(field, "fieldlabel").text = label
        SubElement(field, "fieldentry").text = entry


def build_mcq(item_el: Element, q: dict, _idx: int) -> None:
    _item_metadata(item_el, "multiple_choice_question")

    presentation = SubElement(item_el, "presentation")
    mat = SubElement(SubElement(presentation, "material"), "mattext")
    mat.set("texttype", "text/html")
    mat.text = q["question"]

    resp_lid = SubElement(presentation, "response_lid")
    resp_lid.set("ident", "response1")
    resp_lid.set("rcardinality", "Single")
    render = SubElement(resp_lid, "render_choice")

    letter_to_num: dict[str, str] = {}
    for i, choice_text in enumerate(q["choices"]):
        letter = chr(65 + i)
        num_ident = _make_answer_id()
        letter_to_num[letter] = num_ident
        label = SubElement(render, "response_label")
        label.set("ident", num_ident)
        mattext = SubElement(SubElement(label, "material"), "mattext")
        mattext.set("texttype", "text/html")
        mattext.text = choice_text

    resprocessing = SubElement(item_el, "resprocessing")
    outcomes = SubElement(resprocessing, "outcomes")
    decvar = SubElement(outcomes, "decvar")
    decvar.set("maxvalue", "100"); decvar.set("minvalue", "0")
    decvar.set("varname", "SCORE"); decvar.set("vartype", "Decimal")

    correct_letter = _extract_answer_letter(q["answer"])
    correct_num = letter_to_num.get(correct_letter) or next(iter(letter_to_num.values()), "0")

    respcond = SubElement(resprocessing, "respcondition")
    respcond.set("continue", "No")
    varequal = SubElement(SubElement(respcond, "conditionvar"), "varequal")
    varequal.set("respident", "response1")
    varequal.text = correct_num
    setvar = SubElement(respcond, "setvar")
    setvar.set("action", "Set"); setvar.set("varname", "SCORE"); setvar.text = "100"


def build_true_false(item_el: Element, q: dict, _idx: int) -> None:
    _item_metadata(item_el, "true_false_question")

    presentation = SubElement(item_el, "presentation")
    mat = SubElement(SubElement(presentation, "material"), "mattext")
    mat.set("texttype", "text/html")
    mat.text = q["question"]

    resp_lid = SubElement(presentation, "response_lid")
    resp_lid.set("ident", "response1")
    resp_lid.set("rcardinality", "Single")
    render = SubElement(resp_lid, "render_choice")

    val_to_num: dict[str, str] = {}
    for val, label_text in [("true", "True"), ("false", "False")]:
        num_ident = _make_answer_id()
        val_to_num[val] = num_ident
        label = SubElement(render, "response_label")
        label.set("ident", num_ident)
        mattext = SubElement(SubElement(label, "material"), "mattext")
        mattext.set("texttype", "text/html")
        mattext.text = label_text

    resprocessing = SubElement(item_el, "resprocessing")
    outcomes = SubElement(resprocessing, "outcomes")
    decvar = SubElement(outcomes, "decvar")
    decvar.set("maxvalue", "100"); decvar.set("minvalue", "0")
    decvar.set("varname", "SCORE"); decvar.set("vartype", "Decimal")

    correct_val = q["answer"].strip().lower()
    correct_num = val_to_num.get(correct_val, val_to_num["true"])

    respcond = SubElement(resprocessing, "respcondition")
    respcond.set("continue", "No")
    varequal = SubElement(SubElement(respcond, "conditionvar"), "varequal")
    varequal.set("respident", "response1")
    varequal.text = correct_num
    setvar = SubElement(respcond, "setvar")
    setvar.set("action", "Set"); setvar.set("varname", "SCORE"); setvar.text = "100"


def build_free_response(item_el: Element, q: dict, _idx: int) -> None:
    _item_metadata(item_el, "essay_question")

    presentation = SubElement(item_el, "presentation")
    mat = SubElement(SubElement(presentation, "material"), "mattext")
    mat.set("texttype", "text/html")
    mat.text = q["question"]

    resp_str = SubElement(presentation, "response_str")
    resp_str.set("ident", "response1")
    resp_str.set("rcardinality", "Single")
    render_fib = SubElement(resp_str, "render_fib")
    ans_label = SubElement(render_fib, "response_label")
    ans_label.set("ident", "answer1")
    ans_label.set("rshuffle", "No")


def build_matching(item_el: Element, q: dict, _idx: int) -> None:
    _item_metadata(item_el, "matching_question")

    presentation = SubElement(item_el, "presentation")
    mat = SubElement(SubElement(presentation, "material"), "mattext")
    mat.set("texttype", "text/html")
    mat.text = q["question"]

    pairs = q["pairs"]
    right_num_idents = [_make_answer_id() for _ in pairs]

    for p_idx, pair in enumerate(pairs):
        resp_lid = SubElement(presentation, "response_lid")
        resp_lid.set("ident", f"response_{p_idx + 1}")
        resp_lid.set("rcardinality", "Single")
        left_mat = SubElement(SubElement(resp_lid, "material"), "mattext")
        left_mat.set("texttype", "text/html")
        left_mat.text = pair["left"]
        render = SubElement(resp_lid, "render_choice")
        for r_idx, right_pair in enumerate(pairs):
            label = SubElement(render, "response_label")
            label.set("ident", right_num_idents[r_idx])
            mattext = SubElement(SubElement(label, "material"), "mattext")
            mattext.set("texttype", "text/html")
            mattext.text = right_pair["right"]

    resprocessing = SubElement(item_el, "resprocessing")
    outcomes = SubElement(resprocessing, "outcomes")
    decvar = SubElement(outcomes, "decvar")
    decvar.set("maxvalue", "100"); decvar.set("minvalue", "0")
    decvar.set("varname", "SCORE"); decvar.set("vartype", "Decimal")

    points_each = round(100 / len(pairs), 4) if pairs else 0
    for p_idx in range(len(pairs)):
        respcond = SubElement(resprocessing, "respcondition")
        respcond.set("continue", "Yes")
        varequal = SubElement(SubElement(respcond, "conditionvar"), "varequal")
        varequal.set("respident", f"response_{p_idx + 1}")
        varequal.text = right_num_idents[p_idx]
        setvar = SubElement(respcond, "setvar")
        setvar.set("action", "Add"); setvar.set("varname", "SCORE")
        setvar.text = str(points_each)

_BUILDERS = {
    "mcq": build_mcq,
    "true_false": build_true_false,
    "free_response": build_free_response,
    "matching": build_matching,
}


def json_to_qti_xml(data: dict, quiz_title: str = "Quiz") -> str:

    root = Element("questestinterop")
    root.set("xmlns", "http://www.imsglobal.org/xsd/ims_qtiasiv1p2")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set(
        "xsi:schemaLocation",
        "http://www.imsglobal.org/xsd/ims_qtiasiv1p2 "
        "http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_qtiasiv1p2p1_v1p0.xsd",
    )

    assessment = SubElement(root, "assessment")
    assessment.set("ident", _make_ident())
    assessment.set("title", quiz_title)

    assess_meta = SubElement(assessment, "qtimetadata")
    field = SubElement(assess_meta, "qtimetadatafield")
    SubElement(field, "fieldlabel").text = "cc_maxattempts"
    SubElement(field, "fieldentry").text = "1"

    section = SubElement(assessment, "section")
    section.set("ident", "root_section")

    for idx, q in enumerate(data.get("questions", []), start=1):
        qtype = q.get("type", "")
        builder = _BUILDERS.get(qtype)
        if builder is None:
            print(f"Warning: unknown question type '{qtype}' (question {idx}), skipping.")
            continue

        item = SubElement(section, "item")
        item.set("ident", _make_ident())
        item.set("title", f"Question {idx}")
        builder(item, q, idx)

    indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(root, encoding="unicode")

def _build_manifest(assessment_filename: str) -> str:
    manifest_id = _make_ident()
    resource_id = _make_ident()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{manifest_id}"
  xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
  xmlns:lom="http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1
    http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_imscp_v1p2_v1p0.xsd">
  <metadata>
    <schema>IMS Common Cartridge</schema>
    <schemaversion>1.1.0</schemaversion>
  </metadata>
  <organizations/>
  <resources>
    <resource identifier="{resource_id}"
              type="imsqti_xmlv1p2/imscc_xmlv1p1/assessment"
              href="{assessment_filename}">
      <file href="{assessment_filename}"/>
    </resource>
  </resources>
</manifest>"""

def convert(json_input, output_zip: str = "canvas_quiz.zip", quiz_title: str = "Quiz") -> str:
    if isinstance(json_input, dict):
        data = json_input
    elif isinstance(json_input, list):
        data = {"questions": json_input}
    elif isinstance(json_input, str):
        try:
            parsed = json.loads(json_input)
        except json.JSONDecodeError:
            with open(json_input, "r", encoding="utf-8") as f:
                parsed = json.load(f)
        data = {"questions": parsed} if isinstance(parsed, list) else parsed
    else:
        raise TypeError("json_input must be a dict, list, JSON string, or file path.")

    assessment_filename = "assessment.xml"
    qti_xml = json_to_qti_xml(data, quiz_title=quiz_title)
    manifest_xml = _build_manifest(assessment_filename)

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("imsmanifest.xml", manifest_xml)
        zf.writestr(assessment_filename, qti_xml)

    print(f"QTI package written to: {output_zip}")
    return output_zip

