# Tai lieu Tysor

Thu muc nay chua bo tai lieu su dung va cac so do da doi chieu voi ma nguon hien tai.

## Tep chinh

- `HUONG_DAN_SU_DUNG.md`: huong dan cai dat, van hanh va su dung chi tiet bang tieng Viet.
- `Tysor_Huong_Dan_Su_Dung.docx`: ban Word co diagram PNG nhung truc tiep.
- `DIAGRAMS.md`: nguon Mermaid cua cac diagram de de cap nhat.
- `diagrams/*.png`: anh diagram dung trong tep Word.

## Tao lai ban Word

Chay tu thu muc goc cua du an:

```powershell
py -3.12 scripts/generate_user_guide.py
```

Script chi tao lai cac tep trong `docs/diagrams` va
`docs/Tysor_Huong_Dan_Su_Dung.docx`.
