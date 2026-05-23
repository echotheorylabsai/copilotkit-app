import { z } from "zod";

export const FlightCardProps = z.object({
  title: z.string().describe("Flight card title"),
  airline: z.string().describe("Airline name"),
  origin: z.string().describe("Departure airport code or city"),
  destination: z.string().describe("Arrival airport code or city"),
  departure_time: z.string().describe("Departure time"),
  price: z.string().describe("Price display string e.g. $249"),
});

type FlightCardPropsType = z.infer<typeof FlightCardProps>;

export function FlightCard({
  title,
  airline,
  origin,
  destination,
  departure_time,
  price,
}: FlightCardPropsType) {
  return (
    <div style={{ borderRadius: 8, border: "1px solid #e0e0e0", background: "#fff", padding: 12, marginTop: 8, maxWidth: 340 }}>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>
      <div style={{ border: "1px solid #e0e0e0", borderRadius: 6, padding: 10, fontSize: 14 }}>
        <div style={{ fontWeight: 500 }}>{airline}</div>
        <div>{origin} → {destination}</div>
        <div>Departs: {departure_time}</div>
        <div style={{ fontWeight: 600, marginTop: 4 }}>{price}</div>
      </div>
    </div>
  );
}
