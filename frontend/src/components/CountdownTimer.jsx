import React, { useState, useEffect } from 'react';

export function CountdownTimer({ targetDate }) {
  const [timeLeft, setTimeLeft] = useState({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
    isOver: false,
  });

  useEffect(() => {
    if (!targetDate) return;

    function calculate() {
      const difference = +new Date(targetDate) - +new Date();
      if (difference > 0) {
        setTimeLeft({
          days: Math.floor(difference / (1000 * 60 * 60 * 24)),
          hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
          minutes: Math.floor((difference / 1000 / 60) % 60),
          seconds: Math.floor((difference / 1000) % 60),
          isOver: false,
        });
      } else {
        setTimeLeft({
          days: 0,
          hours: 0,
          minutes: 0,
          seconds: 0,
          isOver: true,
        });
      }
    }

    calculate();
    const interval = setInterval(calculate, 1000);
    return () => clearInterval(interval);
  }, [targetDate]);

  if (timeLeft.isOver) {
    return (
      <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl px-3 py-2 text-center text-rose-300 text-xs font-semibold animate-pulse">
        ⚡️ Стрим должен начаться с минуты на минуту!
      </div>
    );
  }

  const items = [
    { label: 'Дней', value: timeLeft.days, show: timeLeft.days > 0 },
    { label: 'Часов', value: timeLeft.hours, show: true },
    { label: 'Минут', value: timeLeft.minutes, show: true },
    { label: 'Секунд', value: timeLeft.seconds, show: true },
  ].filter((i) => i.show);

  return (
    <div className="flex items-center justify-center gap-2">
      {items.map((item, idx) => (
        <React.Fragment key={item.label}>
          <div className="flex flex-col items-center bg-slate-950/70 border border-indigo-500/30 rounded-lg px-2.5 py-1.5 min-w-[52px] shadow-sm">
            <span className="font-display font-bold text-base text-purple-300 leading-tight">
              {String(item.value).padStart(2, '0')}
            </span>
            <span className="text-[10px] text-slate-400 font-medium tracking-tight">
              {item.label}
            </span>
          </div>
          {idx < items.length - 1 && (
            <span className="text-purple-500/60 font-bold text-xs pb-2">:</span>
          )}
        </React.Fragment>
      ))}
    </div>
  );
}
