# RedirectProof

RedirectProof detects redirect loops, duplicate sources, self-redirects, invalid status codes, and rules hidden behind an earlier catch-all.

Supported formats:

- Netlify-style `_redirects`, including `public/_redirects`;
- `vercel.json` redirects.

It runs offline with no runtime dependencies.

## Install and use

```bash
pip install git+https://github.com/ericz218/redirectproof.git
redirectproof .
redirectproof vercel.json --json
```

## GitHub Action

```yaml
- uses: ericz218/redirectproof@v0.1.0
  with:
    path: .
```

See [`examples/ci.yml`](examples/ci.yml).

## License

MIT
