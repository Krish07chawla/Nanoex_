// Live prices. One WebSocket for the whole app; every page can read the prices.

import { createContext, useContext, useEffect, useState } from "react";
import { api, getToken } from "./api";
import { useAuth } from "./auth";

const LiveContext = createContext({ prices: {}, info: {}, stocks: [], notices: [] });

export function LiveProvider({ children }) {
  const { user } = useAuth();
  const [prices, setPrices] = useState({}); // {TCS: {price, prev_close}}
  const [info, setInfo] = useState({}); // source, delayed, market_open
  const [stocks, setStocks] = useState([]); // [{symbol, name}]
  const [notices, setNotices] = useState([]); // small pop-up messages

  function addNotice(text) {
    const id = Date.now() + Math.random();
    setNotices((old) => [...old, { id, text }]);
    setTimeout(() => setNotices((old) => old.filter((n) => n.id !== id)), 8000);
  }

  function readSnapshot(data) {
    setPrices(data.prices);
    setInfo({ source: data.source, delayed: data.delayed, market_open: data.market_open, updated_at: data.updated_at });
  }

  useEffect(() => {
    if (!user) return;
    let socket;
    let timer;
    let stopped = false;

    api("/market/quotes").then((data) => {
      setStocks(data.stocks);
      readSnapshot(data);
    });

    function connect() {
      const scheme = window.location.protocol === "https:" ? "wss" : "ws";
      socket = new WebSocket(`${scheme}://${window.location.host}/ws?token=${getToken()}`);
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "prices") readSnapshot(data);
        else if (data.message) addNotice(data.message); // order filled or price alert
      };
      socket.onclose = () => {
        if (!stopped) timer = setTimeout(connect, 3000); // try again
      };
    }
    connect();

    return () => {
      stopped = true;
      clearTimeout(timer);
      if (socket) socket.close();
    };
  }, [user]);

  return <LiveContext.Provider value={{ prices, info, stocks, notices }}>{children}</LiveContext.Provider>;
}

export const useLive = () => useContext(LiveContext);
