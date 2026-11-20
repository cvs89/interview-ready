import Image from "next/image";

/** Display the approved artwork without its presentation margins. */
export function BrandLogo() {
  return (
    <span className="relative block aspect-[1840/430] w-[180px] overflow-hidden sm:w-[280px]">
      <Image
        src="/brand/interview-ready-logo-v7.png"
        alt="Interview Ready — Practice before the real interview"
        width={2172}
        height={724}
        sizes="(min-width: 640px) 331px, 213px"
        priority
        className="absolute h-auto max-w-none"
        style={{ width: "118.0435%", left: "-9.2391%", top: "-37.2093%" }}
      />
    </span>
  );
}
