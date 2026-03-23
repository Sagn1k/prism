import { Metadata } from "next";
import CardPageClient from "./client";

interface Props {
  params: { token: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
  return {
    title: "Prism Card",
    description: "Check out this Prism identity card!",
    openGraph: {
      title: "Prism Card",
      description: "See their unique spectrum and archetype on Prism.",
      url: `${baseUrl}/card/${params.token}`,
      type: "website",
      images: [
        {
          url: `${baseUrl}/api/og?token=${params.token}`,
          width: 1200,
          height: 630,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: "Prism Card",
      description: "See their unique spectrum and archetype on Prism.",
    },
  };
}

export default function CardPage({ params }: Props) {
  return <CardPageClient token={params.token} />;
}
