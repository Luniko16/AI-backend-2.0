import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import axios from "axios";
import FormData from "form-data";

dotenv.config();
const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" }));

async function refineWithGPT(userPrompt) {
  const body = {
    model: "gpt-3.5-turbo",
    messages: [
      { role: "system", content: "You are a prompt engineer. Expand short ideas into detailed, visual prompts for image generation. Keep it under 120 words." },
      { role: "user", content: userPrompt }
    ],
    temperature: 0.9
  };
  const res = await axios.post("https://api.openai.com/v1/chat/completions", body, {
    headers: { Authorization: `Bearer ${process.env.OPENAI_API_KEY}` }
  });
  return res.data.choices[0].message.content.trim();
}

async function refineWithDeepSeek(promptText) {
  const body = {
    model: "deepseek-chat",
    messages: [
      { role: "system", content: "Polish the following prompt for AI image generation. Remove camera jargon unless requested. Keep constraints crisp." },
      { role: "user", content: promptText }
    ],
    temperature: 0.8
  };
  const res = await axios.post("https://api.deepseek.com/v1/chat/completions", body, {
    headers: { Authorization: `Bearer ${process.env.DEEPSEEK_API_KEY}` }
  });
  return res.data.choices[0].message.content.trim();
}

async function generateWithStability(finalPrompt, options = {}) {
  const { style = "photorealistic", quality = "high", aspect_ratio = "1:1" } = options;
  const composedPrompt = `${finalPrompt}\nStyle: ${style}\nQuality: ${quality}\nAspect Ratio: ${aspect_ratio}`;
  const url = "https://api.stability.ai/v2beta/stable-image/generate/core";

  const form = new FormData();
  form.append("prompt", composedPrompt);
  form.append("output_format", "png");
  form.append("aspect_ratio", aspect_ratio);

  const res = await axios.post(url, form, {
    responseType: "arraybuffer",
    headers: {
      ...form.getHeaders(),
      Accept: "image/*",
      Authorization: `Bearer ${process.env.STABILITY_API_KEY}`
    },
    maxBodyLength: Infinity,
  });

  const b64 = Buffer.from(res.data, "binary").toString("base64");
  return { imageBase64: b64, mime: "image/png" };
}

app.post("/generate", async (req, res) => {
  try {
    const { userPrompt, style, quality, aspect_ratio } = req.body;
    if (!userPrompt || !userPrompt.trim()) {
      return res.status(400).json({ error: "Prompt is required" });
    }
    const gptRefined = await refineWithGPT(userPrompt);
    const deepseekRefined = await refineWithDeepSeek(gptRefined);
    const finalPrompt = deepseekRefined;

    const { imageBase64, mime } = await generateWithStability(finalPrompt, {
      style, quality, aspect_ratio
    });

    res.json({ finalPrompt, imageBase64, mime });
  } catch (err) {
    console.error(err?.response?.data || err.message);
    res.status(500).json({ error: "Generation failed. Check API keys and quotas." });
  }
});

app.get("/", (_req, res) => res.send("Dual-model backend is running."));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Backend listening on port ${PORT}`));
