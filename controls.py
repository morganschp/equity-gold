"""Allocation inputs that also report changes while a slider is being dragged."""
import streamlit as st

allocation_controls = st.components.v2.component(
    "allocation_controls",
    html="""
      <div class="sliders">
        <label>Gold share of total portfolio
          <output id="gold-value">10%</output>
          <input id="gold" type="range" min="0" max="100" step="1" value="10"
                 aria-label="Gold share of total portfolio">
        </label>
        <label>Emerging markets’ share of equities
          <output id="em-value">10%</output>
          <input id="em" type="range" min="0" max="100" step="1" value="10"
                 aria-label="Emerging markets’ share of equities">
        </label>
      </div>
      <button type="button">Reset to original allocation</button>
    """,
    css="""
      .sliders {display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr)); gap:1rem}
      label {display:grid; grid-template-columns:1fr auto; align-items:start; gap:.4rem; font-size:.9rem}
      output {color:#1f77b4; font-weight:600; font-variant-numeric:tabular-nums}
      input {width:100%; margin:.25rem 0; grid-column:1/-1; accent-color:#1f77b4; cursor:pointer}
      button {margin-top:.8rem; padding:.3rem .7rem; background:white; color:#111; border:1px solid #bbb;
              border-radius:.45rem; font:inherit; font-size:.85rem; cursor:pointer}
      button:hover, button:focus-visible {border-color:#1f77b4; color:#1f77b4}
    """,
    js="""
      export default function({parentElement, setStateValue}) {
        const gold = parentElement.querySelector("#gold");
        const em = parentElement.querySelector("#em");
        const reset = parentElement.querySelector("button");
        const inputs = [gold, em];
        let timer;
        let lastSent = 0;

        function updateLabels() {
          for (const input of inputs) {
            const text = input.value + "%";
            parentElement.querySelector("#" + input.id + "-value").textContent = text;
            input.setAttribute("aria-valuetext", text);
          }
        }
        function publish() {
          clearTimeout(timer);
          lastSent = performance.now();
          setStateValue("weights", {gold: Number(gold.value), em: Number(em.value)});
        }
        function onInput() {
          updateLabels();
          clearTimeout(timer);
          // Send intermediate positions and always commit the final position on release.
          timer = setTimeout(publish, Math.max(0, 350 - (performance.now() - lastSent)));
        }
        for (const input of inputs) {
          input.oninput = onInput;
          input.onchange = publish;
        }
        reset.onclick = () => {
          gold.value = em.value = "10";
          updateLabels();
          publish();
        };
        updateLabels();
      }
    """,
)
