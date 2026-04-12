async function analyze() {
    const urls = document.getElementById("urls").value.split("\n");

    document.getElementById("result").innerText = "Đang xử lý...";
    document.getElementById("strategy").innerText = "";

    const res = await fetch("/analyze", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ urls })
    });

    const data = await res.json();

    document.getElementById("result").innerText =
        JSON.stringify(data.results, null, 2);

    document.getElementById("strategy").innerText =
        data.strategy;
}
