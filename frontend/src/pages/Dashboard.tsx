import { useEffect, useState } from "react";
import {
  getEvents,
  getDriverCount,
  getConstructorCount,
} from "../services/api";
import {
  ArrowUpRight,
  CalendarDays,
  Flag,
  Gauge,
  Trophy,
  Users,
} from "lucide-react";

const recentRaces = [
  {
    round: "01",
    race: "Bahrain Grand Prix",
    circuit: "Bahrain International Circuit",
    date: "05 Mar 2023",
  },
  {
    round: "02",
    race: "Saudi Arabian Grand Prix",
    circuit: "Jeddah Corniche Circuit",
    date: "19 Mar 2023",
  },
  {
    round: "03",
    race: "Australian Grand Prix",
    circuit: "Albert Park Circuit",
    date: "02 Apr 2023",
  },
  {
    round: "04",
    race: "Azerbaijan Grand Prix",
    circuit: "Baku City Circuit",
    date: "30 Apr 2023",
  },
];

export default function Dashboard() {
  const [raceCount, setRaceCount] = useState(0);
  const [driverCount, setDriverCount] = useState(0);
  const [constructorCount, setConstructorCount] = useState(0);

  useEffect(() => {
    getEvents(2023, 1, 0)
      .then((data) => {
        setRaceCount(data.total);
      })
      .catch((error) => {
        console.error("Failed to load race count:", error);
      });

    getDriverCount(2023)
      .then((data) => {
        setDriverCount(data.count);
      })
      .catch((error) => {
        console.error("Failed to load driver count:", error);
      });

    getConstructorCount(2023)
      .then((data) => {
        setConstructorCount(data.count);
      })
      .catch((error) => {
        console.error("Failed to load constructor count:", error);
      });
  }, []);

  const stats = [
    {
      label: "Races",
      value: raceCount.toString(),
      change: "2023",
      icon: Flag,
    },
    {
      label: "Drivers",
      value: driverCount.toString(),
      change: "Active",
      icon: Users,
    },
    {
      label: "Constructors",
      value: constructorCount.toString(),
      change: "Teams",
      icon: Trophy,
    },
    {
      label: "Lap Records",
      value: "24.4K",
      change: "2023",
      icon: Gauge,
    },
  ];

  return (
    <div className="dashboard">
      <section className="page-heading">
        <div>
          <span className="eyebrow">2023 SEASON</span>
          <h2>Race Intelligence</h2>
          <p>
            Monitor race performance, driver statistics and strategy insights.
          </p>
        </div>

        <button className="season-button">
          <CalendarDays size={17} />
          2023 Season
        </button>
      </section>

      <section className="stats-grid">
        {stats.map((stat) => {
          const Icon = stat.icon;

          return (
            <div className="stat-card" key={stat.label}>
              <div className="stat-card-top">
                <div className="stat-icon">
                  <Icon size={19} />
                </div>

                <ArrowUpRight size={17} />
              </div>

              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
              <span className="stat-change">{stat.change}</span>
            </div>
          );
        })}
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">SEASON OVERVIEW</span>
              <h3>Recent Races</h3>
            </div>

            <button className="text-button">View all</button>
          </div>

          <div className="race-list">
            {recentRaces.map((race) => (
              <div className="race-row" key={race.round}>
                <div className="race-round">{race.round}</div>

                <div className="race-info">
                  <strong>{race.race}</strong>
                  <span>{race.circuit}</span>
                </div>

                <div className="race-date">{race.date}</div>

                <ArrowUpRight size={17} />
              </div>
            ))}
          </div>
        </div>

        <div className="panel analyst-panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">AI ANALYST</span>
              <h3>Race Strategy Assistant</h3>
            </div>
          </div>

          <div className="analyst-content">
            <div className="analyst-orb">
              <Gauge size={25} />
            </div>

            <p>
              Ask questions about race pace, tyre strategy, driver
              performance, pit stops and historical F1 data.
            </p>

            <button className="analyst-button">
              Open AI Analyst
              <ArrowUpRight size={16} />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}