import { useTranslation } from "react-i18next";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Api } from "@/api";
import logoImg from "@/assets/logo.png";
import branchImg from "@/assets/branch.png";
import { useEffect } from "react";
import { Button, Credits, Tag, TextInput, Popup, CreditsButton } from "@/components";
import { HeartIcon } from '@heroicons/react/24/solid';
import { isDemo } from "@/api";

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState("");
  const [error, setError] = useState("");
  const timeline = t('timeline', { returnObjects: true }) as Array<{ day: string; desc: string }>;

  const handleLogin = async () => {
    setError("");
    if (!inputValue.trim() && !isDemo) {
      setError("Please enter a password");
      return;
    }
    try {
      const userInfo = await Api.login(inputValue);
      localStorage.setItem('userInfo', JSON.stringify(userInfo));
      navigate("/home");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  };

  useEffect(() => {
    const autoLogin = async () => {
      const userInfo = localStorage.getItem("userInfo");
      if (!userInfo) return;
      try {
        await Api.getUserStats();
        navigate("/home");
      } catch (err) {
        console.log("AutoLogin failed", err)
      }
    };
    void autoLogin();
  }, [navigate]);

  return (
    <div>
      <div className="bg-white flex flex-col items-center min-h-screen">
        <div className="relative flex flex-col items-center min-h-screen w-full overflow-hidden">
          {/*Flowers*/}
          <div className="absolute -top-25.25 -left-35.5 size-81.75 flex items-center justify-center pointer-events-none">
            <img src={branchImg} alt="" className="size-61 rotate-[63.2deg] object-cover" />
          </div>
          <div className="absolute -top-29.5 -right-28.25 size-86 flex items-center justify-center pointer-events-none">
            <img src={branchImg} alt="" className="size-61 rotate-[-136.61deg] object-cover" />
          </div>
          <div className="absolute -bottom-53.5 -left-39.75 size-82.5 flex items-center justify-center pointer-events-none">
            <img src={branchImg} alt="" className="size-61 rotate-[61.62deg] object-cover" />
          </div>
          <div className="absolute -bottom-43 -right-43 size-85.75 flex items-center justify-center pointer-events-none">
            <img src={branchImg} alt="" className="size-61 rotate-[-39.38deg] object-cover" />
          </div>

          <div className="relative flex flex-col items-center gap-2.5 px-2.5 pt-35 pb-10">

            <img src={logoImg} alt="Logo" className="h-20.75 w-19 object-contain shrink-0" />

            <div className="flex flex-col gap-3.75 items-center w-full">
              <h1
                className="text-[50px] text-[#1b2027] text-center"
                style={{ fontWeight: 600 }}
              >
                {t("header")}
              </h1>

              <div className="w-40 h-0.5" style={{ background: "#000000" }}></div>

              <h2
                className="text-[16px] text-center bg-clip-text text-transparent"
                style={{
                  fontWeight: 530,
                  maxWidth: "256px",
                  backgroundImage:
                      "linear-gradient(93deg, #2E263A 24.76%, #796E8F 35.87%, #493B63 47.48%, #69657B 57.57%, #2E263A 75.24%)",
                }}
              >
                {t("caption")}
              </h2>
            </div>
            <div className="flex flex-col w-full gap-2.5 px-4 py-6 sm:px-10 sm:py-10">
              {timeline.map(({ day, desc }) => (
                <div
                    key={day}
                    className="flex items-center justify-between w-full gap-3"
                >
                  <Tag content={day} />

                  <p className="text-[15px] text-black leading-none flex-1 text-right">
                    {desc}
                  </p>
                </div>
              ))}
            </div>
            <div className="flex flex-col gap-6 items-center justify-center pb-15 w-full">
              <TextInput
                value={inputValue}
                width="19.25rem"
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={t("login.placeholder")}
              />

              <Button
                onClick={handleLogin}
              >
                {isDemo ? t("demo.loginButton") : t("login.button")} <HeartIcon className="w-[1.4rem] h-[1.4rem]"/>
              </Button>
              {isDemo && (
                <div className="flex flex-col gap-1">
                  <CreditsButton
                    text="Access to admin panel"
                    onClick={() => window.location.href = "/Affinities-documentation.html"}
                  />
                  <CreditsButton
                    text="Access to ml"
                    onClick={() => navigate("/ml")}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      <Popup
          isOpen={error!=""}
          error = {true}
          onClose={() => window.location.reload()}
          content={error}
      />
      <Credits/>
    </div>
  );
}