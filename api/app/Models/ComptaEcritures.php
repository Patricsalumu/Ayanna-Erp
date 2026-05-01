<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class ComptaEcritures extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'compta_ecritures';
    protected $fillable = ['id', 'journal_id', 'compte_comptable_id', 'debit', 'credit', 'ordre', 'libelle'];
    protected $casts = ['debit' => 'decimal:2', 'credit' => 'decimal:2'];

    public function journal()          { return $this->belongsTo(ComptaJournaux::class, 'journal_id'); }
    public function compteComptable()  { return $this->belongsTo(ComptaComptes::class, 'compte_comptable_id'); }
}
