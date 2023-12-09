const ws = new WebSocket(`wss://127.0.0.1:5003/api/v2/generate`);
ws.onopen = () => {
  const prompt = "A cat sat on";
  const maxLength = 30;
  ws.send(
    JSON.stringify({
      type: "open_inference_session",
      model: "stabilityai/StableBeluga2",
      max_length: maxLength,
    })
  );
  ws.send(
    JSON.stringify({
      type: "generate",
      inputs: prompt,
      max_length: maxLength,
      do_sample: 1,
      temperature: 0.6,
      top_p: 0.9,
    })
  );
  ws.onmessage = (event) => {
    const response = JSON.parse(event.data);
    if (response.ok) {
      if (response.outputs === undefined) {
        console.log("Session opened, generating...");
      } else {
        console.log("Generated: " + prompt + response.outputs);
        ws.close();
      }
    } else {
      console.log("Error: " + response.traceback);
      ws.close();
    }
  };
};
