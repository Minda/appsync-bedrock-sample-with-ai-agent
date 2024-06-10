// LanguageSelector.tsx
import { SelectField, View } from "@aws-amplify/ui-react";
import { useState } from "react";

interface LanguageSelectorProps {
  onLanguageChange: (languageIn: string, languageOut: string) => void;
}

export function LanguageSelector({ onLanguageChange }: LanguageSelectorProps) {
  const [languageIn, setLanguageIn] = useState("English");
  const [languageOut, setLanguageOut] = useState("French");

  const handleLanguageInChange = (language: string) => {
    setLanguageIn(language);
    onLanguageChange(language, languageOut);
  };

  const handleLanguageOutChange = (language: string) => {
    setLanguageOut(language);
    onLanguageChange(languageIn, language);
  };

  return (
    <View>
      <SelectField
        label="Language In"
        value={languageIn}
        onChange={(e) => handleLanguageInChange(e.target.value)}
      >
        <option value="English">English</option>
        <option value="French">French</option>
        <option value="Spanish">Spanish</option>
        <option value="German">German</option>
        <option value="Italian">Italian</option>
        <option value="Ukrainian">Ukrainian</option>
      </SelectField>
      <SelectField
        label="Language Out"
        value={languageOut}
        onChange={(e) => handleLanguageOutChange(e.target.value)}
      >
        <option value="English">English</option>
        <option value="French">French</option>
        <option value="Spanish">Spanish</option>
        <option value="German">German</option>
        <option value="Italian">Italian</option>
        <option value="Ukrainian">Ukrainian</option>
      </SelectField>
    </View>
  );
}