SYSTEM_PROMPT = """ Your job is to convert written articles into podcast scripts that sound natural when read aloud by a single host.

The script must:
- Sound conversational and spoken, not written
- Use short to medium-length sentences
- Flow smoothly with clear transitions
- Be engaging but not sensationalized
- Avoid jargon unless clearly explained
- Never mention the word “article”, “author”, or “this piece”
- Never reference paragraphs, sections, or formatting
- Never include citations or URLs
- Never include stage directions or sound effects

Assume the listener has not read the source material.
"""
ACQUIRED_SYSTEM_PROMPT = """ You are a podcast scriptwriter generating podcast episode transcripts in the style of the Acquired podcast.

Your goal is to produce long-form, deeply researched, narrative business analysis focused on the history, strategy, and outcomes of a company, acquisition, or major business event.

Tone & Voice
- Analytical, calm, thoughtful, and intellectually curious
- Casual, do not sound overly corporate or stuck up, should read like a conversation, not a memo or essay
- Conversational but precise (no hype, no clickbait)
- Assumes an intelligent audience interested in business, technology, and investing
- Neutral and balanced — do not push strong opinions without evidence

Structure

Write the episode as a full podcast script, including:
	1.	Cold open
	•	A compelling question, tension, or paradox
	•	Briefly frames why this story matters
	2.	Introduction
	•	Hosts introduce the company/event and why it’s worth studying
	•	High-level overview of the outcome (success, failure, or ambiguity)
	3.	Founding & Early Context
	•	Industry backdrop at the time
	•	Founders’ motivations and early decisions
	•	Initial product-market fit challenges
	4.	Key Inflection Points
	•	Strategic decisions, pivots, acquisitions, or turning points
	•	Competitive dynamics and market structure
	•	Capital, incentives, and constraints
	5.	The Acquisition / Outcome (if applicable)
	•	Why the deal happened
	•	What each side believed they were buying or achieving
	•	Valuation logic and strategic rationale
	6.	Post-Event Analysis
	•	What worked, what didn’t
	•	Integration challenges or scaling effects
	•	Second-order consequences
	7.	Lessons & Frameworks
	•	Generalizable insights for business, strategy, or investing
	•	Clear separation between facts and interpretation
	8.	Closing Reflection
	•	Zooms out to industry-level or long-term implications

Style Constraints
	•	No sound effects, ads, or sponsor reads
	•	No exaggerated drama or storytelling clichés
	•	No first-person roleplay as a romantic or personal character
	•	Avoid excessive jokes or slang
	•	Prefer clear explanations over cleverness

Formatting
	•	Write in dialogue format (e.g., Ben: / David:), but do not overdo back-and-forth
	•	Paragraph-level turns, not short quips
	•	Use clear section breaks (e.g., [Founding], [Inflection Point])

Research Expectations
	•	Ground claims in plausible business logic and historical context
	•	When uncertain, acknowledge ambiguity rather than fabricating details
	•	Do not invent quotes or financial figures unless explicitly told to

The final output should read like a real Acquired episode transcript: long, structured, thoughtful, and insight-dense.
"""

def build_user_prompt(article_text: str) -> str:
    return f"""Convert the following source text into a podcast script.

Use ONLY the information in the source material.
Do NOT introduce facts, examples, or claims that are not supported by the sources.
Do NOT come up with a name for the podcast.

Requirements:
- Length: 3-5 minutes when read aloud
- Tone: intelligent, calm, and engaging
- Style: clear explanations, natural pacing, and smooth transitions
- Structure:
  1. A brief hook that introduces the topic
  2. A clear introduction to what will be discussed
  3. The main content, explained step by step
  4. A concise closing that summarizes the key idea

Write exactly as a podcast host would speak.

SOURCE TEXT:
<
{article_text}
>>>
"""

def build_acquired_user_prompt(article_text: str) -> str:
    return f"""Using the source material below, write a podcast episode transcript in the style of the Acquired podcast (between two hosts Ben and David).

Use ONLY the information provided in the source material.
Do NOT introduce facts, numbers, quotes, or events that are not supported by the sources.
If the sources are incomplete or ambiguous, acknowledge uncertainty rather than filling gaps.

Requirements:
- Length: approximately 5–10 minutes when read aloud
- Tone: calm, thoughtful, analytical
- Audience: intelligent listeners interested in business, technology, and strategy
- Style: clear explanations, deliberate pacing, minimal fluff, no hype

Structure the episode as follows:
1. Cold open that frames a central question, tension, or paradox
2. Introduction explaining why this story matters
3. Background and historical context
4. Key strategic decisions, incentives, and tradeoffs
5. Outcomes and second-order effects
6. Clear takeaways or lessons

Formatting:
- Write in spoken-language podcast transcript form
- Use natural paragraph-length turns (not short dialogue quips)
- You may use host labels (e.g., Ben:, David:) sparingly, but focus on substance

SOURCE MATERIAL:
<<<
{article_text}
>>>
"""
# For Mistral
# def generate_script(source_material: str, model, tokenizer):
#     try:
#         # Create the message format
#         messages = [
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": build_user_prompt(source_material)}
#         ]

#         # Apply chat template and generate
#         inputs = tokenizer.apply_chat_template(
#             messages,
#             tokenize=True,
#             add_generation_prompt=True,
#             return_tensors="pt"
#         ).to("mps" if torch.backends.mps.is_available() else "cpu")

#         # Generate the response
#         outputs = model.generate(
#             input_ids=inputs,
#             max_new_tokens=2048,
#             use_cache=True,
#             temperature=0.7,
#             do_sample=True,
#             top_p=0.9,
#             repetition_penalty=1.1
#         )

#         # Decoding output
#         full_response = tokenizer.decode(outputs[0], skip_special_tokens=False)

#         # Extract only assistant's response
#         if "[/INST]" in full_response:
#             script = full_response.split("[/INST]")[-1].strip()
#             # Remove trailing </s> token
#             script = script.replace("<s/>", "").strip()
#         else:
#             # Fallback: skip_special_tokens=True
#             script = tokenizer.decode(outputs[0], skip_special_tokens=True)

#             if ">>>" in script:
#                 script = script.split(">>>")[-1].strip()
        
#         return script
#     except Exception as e:
#         raise

# For Llama-8B
def generate_script(source_material: str, model, tokenizer):
    try:
        device = model.device  # Use the device the model is on
        
        # Create the message format
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_acquired_user_prompt(source_material)}
        ]

        # Apply chat template
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(device)

        # Generate
        outputs = model.generate(
            input_ids=inputs,
            max_new_tokens=2048,
            use_cache=True,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id
        )

        # Decode only the new tokens (exclude the prompt)
        prompt_length = inputs.shape[1]
        generated_tokens = outputs[0][prompt_length:]
        script = tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        return script.strip()
        
    except Exception as e:
        print(f"Error generating script: {e}")
        raise