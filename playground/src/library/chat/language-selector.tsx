import React, { useEffect } from "react";
import { SelectField, View } from "@aws-amplify/ui-react";

interface LanguageSelectorProps {
  languageIn: string;
  languageOut: string;
  onLanguageChange: (languageIn: string, languageOut: string) => void;
}

export function LanguageSelector({ languageIn, languageOut, onLanguageChange }: LanguageSelectorProps) {
  useEffect(() => {
    console.log('LanguageSelector mounted/updated - In:', languageIn, 'Out:', languageOut);
  }, [languageIn, languageOut]);

  const handleLanguageInChange = (newLanguageIn: string) => {
    console.log('handleLanguageInChange called with:', newLanguageIn);
    onLanguageChange(newLanguageIn, languageOut);
  };

  const handleLanguageOutChange = (newLanguageOut: string) => {
    console.log('handleLanguageOutChange called with:', newLanguageOut);
    onLanguageChange(languageIn, newLanguageOut);
  };

  console.log('LanguageSelector rendering - In:', languageIn, 'Out:', languageOut);

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